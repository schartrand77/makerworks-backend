# MakerWorks CLI

The MakerWorks command-line interface exposes common maintenance tasks. Once the
package is installed (e.g. via `pip install -e .`) the `mw` command becomes
available.

Run `mw --help` to view top level options.

## Commands

### `mw update alembic [REVISION]`
Run Alembic migrations up to the given revision (`head` by default).

### `mw db init`
Create all database tables.

### `mw db drop`
Drop all database tables **use with caution**.

### `mw db subset`
Create only the `User` and `Filament` tables. Useful for test setups.

### `mw users list`
Display all users and their current roles.

### `mw users change-role --email EMAIL --role {admin,user}`
Change a specific user's role.

### `mw seed filaments`
Insert a small set of example filaments into the database.

