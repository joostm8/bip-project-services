from __future__ import annotations

import json
import random
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import paho.mqtt.client as mqtt

from ship_simulator.container import Container
from ship_simulator.shipsimulation import ShipSimulation


# ---------- SQLite helpers (adapted from labs/database-lab/0-sqlite-primer.ipynb) ----------

create_container_table_query = """
CREATE TABLE IF NOT EXISTS container (
    container_id INTEGER PRIMARY KEY,
    weight_kg REAL NOT NULL CHECK (weight_kg > 0)
);
"""

create_ship_table_query = """
CREATE TABLE IF NOT EXISTS ship (
    ship_id INTEGER PRIMARY KEY,
    roll_deg REAL NOT NULL,
    draft_m REAL NOT NULL CHECK (draft_m >= 0)
);
"""

create_wharf_slot_table_query = """
CREATE TABLE IF NOT EXISTS wharf_slot (
    slot_id INTEGER PRIMARY KEY,
    row INTEGER NOT NULL,
    col INTEGER NOT NULL,
    occupancy TEXT NOT NULL CHECK (occupancy IN ('empty', 'occupied')),
    container_id INTEGER UNIQUE,
    FOREIGN KEY (container_id) REFERENCES container(container_id),
    CHECK (
        (occupancy = 'empty' AND container_id IS NULL)
        OR
        (occupancy = 'occupied' AND container_id IS NOT NULL)
    ),
    UNIQUE (row, col)
);
"""

create_ship_slot_table_query = """
CREATE TABLE IF NOT EXISTS ship_slot (
    slot_id INTEGER NOT NULL,
    ship_id INTEGER NOT NULL,
    row INTEGER NOT NULL,
    col INTEGER NOT NULL,
    occupancy TEXT NOT NULL CHECK (occupancy IN ('empty', 'occupied')),
    container_id INTEGER UNIQUE,
    PRIMARY KEY (ship_id, slot_id),
    FOREIGN KEY (ship_id) REFERENCES ship(ship_id),
    FOREIGN KEY (container_id) REFERENCES container(container_id),
    CHECK (
        (occupancy = 'empty' AND container_id IS NULL)
        OR
        (occupancy = 'occupied' AND container_id IS NOT NULL)
    ),
    UNIQUE (ship_id, row, col)
);
"""

create_wharf_slot_cross_presence_trigger_query = """
CREATE TRIGGER IF NOT EXISTS trg_wharf_container_not_on_ship_insert
BEFORE INSERT ON wharf_slot
FOR EACH ROW
WHEN NEW.occupancy = 'occupied' AND NEW.container_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM ship_slot
            WHERE container_id = NEW.container_id
        ) THEN RAISE(ABORT, 'Container already assigned to ship_slot')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_wharf_container_not_on_ship_update
BEFORE UPDATE OF container_id, occupancy ON wharf_slot
FOR EACH ROW
WHEN NEW.occupancy = 'occupied' AND NEW.container_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM ship_slot
            WHERE container_id = NEW.container_id
        ) THEN RAISE(ABORT, 'Container already assigned to ship_slot')
    END;
END;
"""

create_ship_slot_cross_presence_trigger_query = """
CREATE TRIGGER IF NOT EXISTS trg_ship_container_not_on_wharf_insert
BEFORE INSERT ON ship_slot
FOR EACH ROW
WHEN NEW.occupancy = 'occupied' AND NEW.container_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM wharf_slot
            WHERE container_id = NEW.container_id
        ) THEN RAISE(ABORT, 'Container already assigned to wharf_slot')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_ship_container_not_on_wharf_update
BEFORE UPDATE OF container_id, occupancy ON ship_slot
FOR EACH ROW
WHEN NEW.occupancy = 'occupied' AND NEW.container_id IS NOT NULL
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM wharf_slot
            WHERE container_id = NEW.container_id
        ) THEN RAISE(ABORT, 'Container already assigned to wharf_slot')
    END;
END;
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    complete_query = (
        create_container_table_query
        + create_ship_table_query
        + create_wharf_slot_table_query
        + create_ship_slot_table_query
        + create_wharf_slot_cross_presence_trigger_query
        + create_ship_slot_cross_presence_trigger_query
    )
    connection.executescript(complete_query)


def seed_wharf_slots(connection: sqlite3.Connection, rows: int = 2, cols: int = 3) -> None:
    slot_id = 1
    with connection:
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO wharf_slot(slot_id, row, col, occupancy, container_id)
                    VALUES (?, ?, ?, 'empty', NULL)
                    """,
                    (slot_id, row, col),
                )
                slot_id += 1


def seed_ship_slots(connection: sqlite3.Connection, ship_id: int, rows: int = 2, cols: int = 3) -> None:
    slot_id = 1
    with connection:
        for row in range(1, rows + 1):
            for col in range(1, cols + 1):
                connection.execute(
                    """
                    INSERT OR IGNORE INTO ship_slot(slot_id, ship_id, row, col, occupancy, container_id)
                    VALUES (?, ?, ?, ?, 'empty', NULL)
                    """,
                    (slot_id, ship_id, row, col),
                )
                slot_id += 1


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()


def intake_container(connection: sqlite3.Connection, container_id: int, weight_kg: float) -> None:
    with connection:
        connection.execute(
            "INSERT INTO container(container_id, weight_kg) VALUES (?, ?)",
            (container_id, weight_kg),
        )


def add_ship(connection: sqlite3.Connection, ship_id: int, roll_deg: float, draft_m: float) -> None:
    with connection:
        connection.execute(
            "INSERT INTO ship(ship_id, roll_deg, draft_m) VALUES (?, ?, ?)",
            (ship_id, roll_deg, draft_m),
        )


def update_ship_state(connection: sqlite3.Connection, ship_id: int, roll_deg: float, draft_m: float) -> None:
    with connection:
        cursor = connection.execute(
            """
            UPDATE ship
            SET roll_deg = ?, draft_m = ?
            WHERE ship_id = ?
            """,
            (roll_deg, draft_m, ship_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Unknown ship_id: {ship_id}")


def place_container_in_wharf_slot(connection: sqlite3.Connection, container_id: int, slot_id: int) -> None:
    with connection:
        cursor = connection.execute(
            """
            UPDATE wharf_slot
            SET occupancy = 'occupied', container_id = ?
            WHERE slot_id = ? AND occupancy = 'empty'
            """,
            (container_id, slot_id),
        )
        if cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                f"Cannot place container {container_id} in wharf slot {slot_id}: slot does not exist or is not empty"
            )


def place_container_on_ship_slot(
    connection: sqlite3.Connection,
    container_id: int,
    ship_id: int,
    slot_id: int,
) -> None:
    with connection:
        cursor = connection.execute(
            """
            UPDATE ship_slot
            SET occupancy = 'occupied', container_id = ?
            WHERE ship_id = ? AND slot_id = ? AND occupancy = 'empty'
            """,
            (container_id, ship_id, slot_id),
        )
        if cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                f"Cannot place container {container_id} in ship slot {slot_id}: slot does not exist or is not empty"
            )


def load_container_onto_ship(
    connection: sqlite3.Connection,
    container_id: int,
    ship_id: int,
    slot_id: int,
) -> None:
    with connection:
        source_cursor = connection.execute(
            """
            UPDATE wharf_slot
            SET occupancy = 'empty', container_id = NULL
            WHERE container_id = ? AND occupancy = 'occupied'
            """,
            (container_id,),
        )
        if source_cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                f"Cannot load container {container_id}: it is not currently in an occupied wharf slot"
            )

        target_cursor = connection.execute(
            """
            UPDATE ship_slot
            SET occupancy = 'occupied', container_id = ?
            WHERE ship_id = ? AND slot_id = ? AND occupancy = 'empty'
            """,
            (container_id, ship_id, slot_id),
        )
        if target_cursor.rowcount == 0:
            raise sqlite3.IntegrityError(
                f"Cannot load into ship_id={ship_id}, slot_id={slot_id}: slot does not exist or is not empty"
            )


def list_wharf_state(connection: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT slot_id, row, col, occupancy, container_id
        FROM wharf_slot
        ORDER BY row, col
        """
    ).fetchall()
    return [dict(row) for row in rows]


def list_ship_state(connection: sqlite3.Connection, ship_id: int) -> List[Dict[str, Any]]:
    rows = connection.execute(
        """
        SELECT ship_id, slot_id, row, col, occupancy, container_id
        FROM ship_slot
        WHERE ship_id = ?
        ORDER BY row, col
        """,
        (ship_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def find_container(connection: sqlite3.Connection, container_id: int) -> Optional[Dict[str, Any]]:
    row = connection.execute(
        """
        SELECT 'wharf' AS area, slot_id, row, col
        FROM wharf_slot
        WHERE container_id = ?
        UNION ALL
        SELECT 'ship' AS area, slot_id, row, col
        FROM ship_slot
        WHERE container_id = ?
        """,
        (container_id, container_id),
    ).fetchone()
    return dict(row) if row else None


# ---------- Domain model ----------

@dataclass(frozen=True)
class ManifestEntry:
    container_id: int
    weight_kg: float
    slot_id: int


@dataclass
class SolutionConfig:
    db_path: Path
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_base_topic: str = "bip/mqtt-lab"
    system_id: str = "crane-pi-1"
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_ca_cert_path: Optional[str] = None
    ship_id: int = 1
    dry_run: bool = False

    # retry/synchronization
    base_timeout_s: float = 30.0
    max_retries: int = 1

    # conveyor behavior
    poll_interval_s: float = 0.75
    camera_move_duration_ms: int = 2500
    camera_move_direction: str = "B"
    accept_move_direction: str = "B"
    reject_move_direction: str = "F"

    # crane positions in mm (from measured setup)
    conveyor_pickup_x_mm: int = 0
    pickup_height_mm: int = 86
    travel_height_mm: int = 200
    drop_height_row1_mm: int = 35
    row2_drop_extra_mm: int = 22

    ship_start_x_mm: int = 360
    wharf_start_x_mm: int = 200
    slot_x_offset_mm: int = 40


class MqttRequestResponseClient:
    def __init__(self, config: SolutionConfig):
        self.config = config
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if config.mqtt_username:
            self.client.username_pw_set(config.mqtt_username, config.mqtt_password)
        if config.mqtt_ca_cert_path:
            self.client.tls_set(ca_certs=config.mqtt_ca_cert_path)

        self._connected = threading.Event()
        self._pending_lock = threading.Lock()
        self._pending: Dict[str, Dict[str, Any]] = {}

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def connect(self) -> None:
        self.client.connect(self.config.mqtt_host, self.config.mqtt_port, keepalive=60)
        self.client.loop_start()
        if not self._connected.wait(timeout=8.0):
            raise TimeoutError("MQTT connect timeout")

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code != 0:
            return
        response_topic = (
            f"{self.config.mqtt_base_topic}/{self.config.system_id}/res/#"
        )
        client.subscribe(response_topic, qos=2)
        self._connected.set()

    def _on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split("/")
        if len(topic_parts) < 2:
            return

        cmd_id = topic_parts[-2]
        command = topic_parts[-1]

        try:
            payload_text = msg.payload.decode("utf-8")
            payload = json.loads(payload_text) if payload_text.strip() else {}
        except Exception:
            payload = {}

        with self._pending_lock:
            pending = self._pending.get(cmd_id)
            if pending is None:
                return
            pending["responses"][command] = payload
            pending["event"].set()

    def request(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}

        last_error: Optional[Exception] = None
        for _attempt in range(self.config.max_retries + 1):
            cmd_id = uuid.uuid4().hex
            event = threading.Event()
            with self._pending_lock:
                self._pending[cmd_id] = {"event": event, "responses": {}}

            topic = (
                f"{self.config.mqtt_base_topic}/{self.config.system_id}/req/{cmd_id}/{command}"
            )
            self.client.publish(topic, json.dumps(payload), qos=2)

            if event.wait(timeout=self.config.base_timeout_s):
                with self._pending_lock:
                    responses = self._pending.pop(cmd_id, {}).get("responses", {})
                if command in responses:
                    return responses[command]
                if responses:
                    # if service returns a different terminal command key, use first response
                    return next(iter(responses.values()))
                return {}

            with self._pending_lock:
                self._pending.pop(cmd_id, None)
            last_error = TimeoutError(f"No response for command {command}")

        if last_error is None:
            last_error = RuntimeError("Unknown request failure")
        raise last_error


class HarbourTeacherSolution:
    def __init__(self, config: SolutionConfig):
        self.config = config
        self.mqtt = None if config.dry_run else MqttRequestResponseClient(config)
        self.manifest: Dict[int, ManifestEntry] = {}
        self.loaded_container_ids: set[int] = set()

        # ship has 3 columns x 2 rows according to requirements
        self.ship_sim = ShipSimulation(width_slots=3, height_slots=2)

        # dry-run conveyor/camera state machine
        self._dry_queue: List[int] = []
        self._dry_current_container_id: Optional[int] = None
        self._dry_sensor_has_container = False

    def initialize(self, seed: Optional[int] = None) -> List[ManifestEntry]:
        if seed is not None:
            random.seed(seed)

        reset_database(self.config.db_path)
        with get_connection(self.config.db_path) as connection:
            create_schema(connection)
            seed_wharf_slots(connection, rows=2, cols=3)
            add_ship(connection, self.config.ship_id, roll_deg=0.0, draft_m=0.0)
            seed_ship_slots(connection, ship_id=self.config.ship_id, rows=2, cols=3)

        entries = self._generate_manifest_entries()
        self.manifest = {entry.container_id: entry for entry in entries}
        self.loaded_container_ids = set()

        if self.config.dry_run:
            # Put top-row targets first to force temporary wharf placement/cascade, and prepend one unknown container.
            sorted_entries = sorted(entries, key=lambda item: item.slot_id, reverse=True)
            self._dry_queue = [999] + [item.container_id for item in sorted_entries]
            self._dry_current_container_id = None
            self._dry_sensor_has_container = False

        self._sync_ship_state_to_db()
        return entries

    def connect(self) -> None:
        if self.mqtt is not None:
            self.mqtt.connect()

    def close(self) -> None:
        if self.mqtt is not None:
            self.mqtt.close()

    def _generate_manifest_entries(self) -> List[ManifestEntry]:
        container_ids = random.sample(range(1, 11), k=6)
        slot_ids = random.sample(range(1, 7), k=6)
        entries: List[ManifestEntry] = []
        for container_id, slot_id in zip(container_ids, slot_ids):
            weight = float(random.randint(3700, 30480))
            entries.append(
                ManifestEntry(
                    container_id=container_id,
                    weight_kg=weight,
                    slot_id=slot_id,
                )
            )
        return entries

    @staticmethod
    def slot_id_to_row_col(slot_id: int) -> Tuple[int, int]:
        if slot_id < 1 or slot_id > 6:
            raise ValueError(f"Invalid slot_id: {slot_id}")
        row = ((slot_id - 1) // 3) + 1
        col = ((slot_id - 1) % 3) + 1
        return row, col

    def _is_ship_slot_accessible(self, row: int, col: int) -> bool:
        if row == 1:
            return True

        # row 2 is only accessible if row 1 same column is occupied
        with get_connection(self.config.db_path) as connection:
            below = connection.execute(
                """
                SELECT occupancy
                FROM ship_slot
                WHERE ship_id = ? AND row = 1 AND col = ?
                """,
                (self.config.ship_id, col),
            ).fetchone()
        return bool(below and below["occupancy"] == "occupied")

    def _container_exists_in_db(self, container_id: int) -> bool:
        with get_connection(self.config.db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM container WHERE container_id = ?",
                (container_id,),
            ).fetchone()
        return row is not None

    def _first_free_wharf_slot(self) -> Optional[Dict[str, Any]]:
        with get_connection(self.config.db_path) as connection:
            row = connection.execute(
                """
                SELECT slot_id, row, col
                FROM wharf_slot
                WHERE occupancy = 'empty'
                ORDER BY row ASC, col ASC
                LIMIT 1
                """
            ).fetchone()
        return dict(row) if row else None

    def _find_ship_slot_id(self, row: int, col: int) -> int:
        with get_connection(self.config.db_path) as connection:
            result = connection.execute(
                """
                SELECT slot_id
                FROM ship_slot
                WHERE ship_id = ? AND row = ? AND col = ?
                """,
                (self.config.ship_id, row, col),
            ).fetchone()
        if result is None:
            raise ValueError(f"No ship slot for row={row}, col={col}")
        return int(result["slot_id"])

    def _row_drop_height(self, row: int) -> int:
        if row == 1:
            return self.config.drop_height_row1_mm
        return self.config.drop_height_row1_mm + self.config.row2_drop_extra_mm

    def _slot_x_ship(self, col: int) -> int:
        return self.config.ship_start_x_mm + (col - 1) * self.config.slot_x_offset_mm

    def _slot_x_wharf(self, col: int) -> int:
        return self.config.wharf_start_x_mm + (col - 1) * self.config.slot_x_offset_mm

    def _request(self, command: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.config.dry_run:
            return self._dry_run_request(command, payload or {})
        if self.mqtt is None:
            raise RuntimeError("MQTT client is not initialized")
        return self.mqtt.request(command, payload or {})

    def _dry_run_request(self, command: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if command == "G4":
            if not self._dry_sensor_has_container and self._dry_current_container_id is None and self._dry_queue:
                self._dry_current_container_id = self._dry_queue.pop(0)
                self._dry_sensor_has_container = True
            return {
                "START_SENSOR": 0,
                "END_SENSOR": 0 if self._dry_sensor_has_container else 1,
                "PULSE_COUNT": 0,
            }

        if command == "G2":
            return {}

        if command == "aruco-id":
            if self._dry_current_container_id is None:
                return {"id": []}
            return {"id": [self._dry_current_container_id]}

        if command == "G3":
            # Direction does not change behavior in dry-run; both accept and reject clear conveyor occupancy.
            _ = payload.get("dir")
            self._dry_current_container_id = None
            self._dry_sensor_has_container = False
            return {}

        if command == "hoist":
            return {"height": float(payload.get("height", 0)), "result": "success"}

        if command == "move":
            return {"position": float(payload.get("position", 0)), "result": "success"}

        if command == "G6":
            return {}

        return {}

    # ---------- MQTT commands ----------

    def conveyor_state(self) -> Dict[str, Any]:
        return self._request("G4", {})

    def conveyor_move_duration(self, direction: str, duration_ms: int) -> Dict[str, Any]:
        return self._request("G2", {"dir": direction, "duration": int(duration_ms)})

    def conveyor_move_until_sensor(self, direction: str) -> Dict[str, Any]:
        return self._request("G3", {"dir": direction})

    def camera_scan(self) -> Dict[str, Any]:
        return self._request("aruco-id", {})

    def hoist(self, height_mm: int) -> Dict[str, Any]:
        return self._request("hoist", {"height": int(height_mm)})

    def move_cart(self, position_mm: int) -> Dict[str, Any]:
        return self._request("move", {"position": int(position_mm)})

    def electromagnet(self, enabled: bool) -> Dict[str, Any]:
        return self._request("G6", {"on/off": 1 if enabled else 0})

    # ---------- Sequenced crane actions ----------

    def _pick_from_conveyor(self) -> None:
        self.hoist(self.config.travel_height_mm)
        self.move_cart(self.config.conveyor_pickup_x_mm)
        self.hoist(self.config.pickup_height_mm)
        self.electromagnet(True)
        self.hoist(self.config.travel_height_mm)

    def _drop_to_ship_slot(self, row: int, col: int) -> None:
        self.move_cart(self._slot_x_ship(col))
        self.hoist(self._row_drop_height(row))
        self.electromagnet(False)
        self.hoist(self.config.travel_height_mm)

    def _drop_to_wharf_slot(self, row: int, col: int) -> None:
        self.move_cart(self._slot_x_wharf(col))
        self.hoist(self._row_drop_height(row))
        self.electromagnet(False)
        self.hoist(self.config.travel_height_mm)

    def _pick_from_wharf_slot(self, row: int, col: int) -> None:
        self.hoist(self.config.travel_height_mm)
        self.move_cart(self._slot_x_wharf(col))
        self.hoist(self._row_drop_height(row))
        self.electromagnet(True)
        self.hoist(self.config.travel_height_mm)

    def _update_ship_sim_for_add(self, entry: ManifestEntry) -> None:
        row, col = self.slot_id_to_row_col(entry.slot_id)
        x_slot = col - 1
        y_slot = row - 1

        container = Container(weight=entry.weight_kg, container_id=f"CONT{entry.container_id}")
        success, message, _heel = self.ship_sim.process_container_add(
            container=container,
            x_slot=x_slot,
            y_slot=y_slot,
        )
        if not success:
            raise RuntimeError(f"Ship simulation rejected placement: {message}")

        self._sync_ship_state_to_db()

    def _sync_ship_state_to_db(self) -> None:
        telemetry = self.ship_sim.get_telemetry()
        roll = float(telemetry.get("heel_angle", 0.0))
        draught = float(telemetry.get("draught", 0.0))

        with get_connection(self.config.db_path) as connection:
            update_ship_state(connection, self.config.ship_id, roll_deg=roll, draft_m=draught)

    def _accept_from_conveyor_to_ship(self, entry: ManifestEntry) -> None:
        row, col = self.slot_id_to_row_col(entry.slot_id)
        ship_slot_id = self._find_ship_slot_id(row, col)

        if not self._container_exists_in_db(entry.container_id):
            with get_connection(self.config.db_path) as connection:
                intake_container(connection, entry.container_id, entry.weight_kg)

        self._pick_from_conveyor()
        self._drop_to_ship_slot(row, col)

        with get_connection(self.config.db_path) as connection:
            place_container_on_ship_slot(
                connection,
                container_id=entry.container_id,
                ship_id=self.config.ship_id,
                slot_id=ship_slot_id,
            )

        self.loaded_container_ids.add(entry.container_id)
        self._update_ship_sim_for_add(entry)

    def _accept_from_conveyor_to_wharf(self, entry: ManifestEntry) -> None:
        slot = self._first_free_wharf_slot()
        if slot is None:
            raise RuntimeError("Wharf is full, cannot temporarily store container")

        if not self._container_exists_in_db(entry.container_id):
            with get_connection(self.config.db_path) as connection:
                intake_container(connection, entry.container_id, entry.weight_kg)

        self._pick_from_conveyor()
        self._drop_to_wharf_slot(row=int(slot["row"]), col=int(slot["col"]))

        with get_connection(self.config.db_path) as connection:
            place_container_in_wharf_slot(connection, entry.container_id, slot_id=int(slot["slot_id"]))

    def _cascade_wharf_to_ship(self, on_each_move: Optional[Callable[[], None]] = None) -> List[int]:
        moved: List[int] = []

        # repeat until no additional manifest container can move from wharf to ship
        while True:
            moved_in_pass = False
            for entry in sorted(self.manifest.values(), key=lambda e: e.slot_id):
                if entry.container_id in self.loaded_container_ids:
                    continue

                row, col = self.slot_id_to_row_col(entry.slot_id)
                if not self._is_ship_slot_accessible(row, col):
                    continue

                with get_connection(self.config.db_path) as connection:
                    location = find_container(connection, entry.container_id)

                if not location or location.get("area") != "wharf":
                    continue

                ship_slot_id = self._find_ship_slot_id(row, col)

                self._pick_from_wharf_slot(row=int(location["row"]), col=int(location["col"]))
                self._drop_to_ship_slot(row=row, col=col)

                with get_connection(self.config.db_path) as connection:
                    load_container_onto_ship(
                        connection,
                        container_id=entry.container_id,
                        ship_id=self.config.ship_id,
                        slot_id=ship_slot_id,
                    )

                self.loaded_container_ids.add(entry.container_id)
                self._update_ship_sim_for_add(entry)

                if on_each_move is not None:
                    on_each_move()

                moved.append(entry.container_id)
                moved_in_pass = True

            if not moved_in_pass:
                break

        return moved

    # ---------- utility outputs for notebook ----------

    def manifest_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for entry in sorted(self.manifest.values(), key=lambda e: e.slot_id):
            row, col = self.slot_id_to_row_col(entry.slot_id)
            rows.append(
                {
                    "container_id": entry.container_id,
                    "weight_kg": entry.weight_kg,
                    "slot_id": entry.slot_id,
                    "row": row,
                    "col": col,
                }
            )
        return rows

    def show_ascii_state(self) -> None:
        with get_connection(self.config.db_path) as connection:
            wharf = list_wharf_state(connection)
            ship = list_ship_state(connection, self.config.ship_id)
            ship_state = connection.execute(
                "SELECT roll_deg, draft_m FROM ship WHERE ship_id = ?",
                (self.config.ship_id,),
            ).fetchone()

        print("Ship attitude")
        if ship_state:
            print(f"  roll_deg={ship_state['roll_deg']:.3f} draft_m={ship_state['draft_m']:.3f}")
        print("")

        print("Wharf occupancy (2x3)")
        self._print_grid(wharf)

        print("Ship occupancy (2x3)")
        self._print_grid(ship)

    @staticmethod
    def _print_grid(rows: List[Dict[str, Any]]) -> None:
        by_position = {(row["row"], row["col"]): row for row in rows}
        for r in [1, 2]:
            line: List[str] = []
            for c in [1, 2, 3]:
                slot = by_position.get((r, c))
                if slot and slot.get("occupancy") == "occupied":
                    cid = slot.get("container_id")
                    line.append(f"{cid:>2}")
                else:
                    line.append(" .")
            print(f"  row {r}: " + " | ".join(line))


def build_solution(
    db_path: str = "harbour-terminal-solution.sqlite",
    mqtt_host: str = "localhost",
    mqtt_port: int = 1883,
    mqtt_base_topic: str = "bip/mqtt-lab",
    system_id: str = "crane-pi-1",
    mqtt_username: Optional[str] = None,
    mqtt_password: Optional[str] = None,
    mqtt_ca_cert_path: Optional[str] = None,
    ship_id: int = 1,
    seed: Optional[int] = None,
    dry_run: bool = False,
) -> HarbourTeacherSolution:
    config = SolutionConfig(
        db_path=Path(db_path),
        mqtt_host=mqtt_host,
        mqtt_port=mqtt_port,
        mqtt_base_topic=mqtt_base_topic,
        system_id=system_id,
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_ca_cert_path=mqtt_ca_cert_path,
        ship_id=ship_id,
        dry_run=dry_run,
    )
    solution = HarbourTeacherSolution(config)
    solution.initialize(seed=seed)
    return solution
