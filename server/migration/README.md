# Migrations

Database schema history for the Notes API, managed by **Flask-Migrate**
(a wrapper around Alembic). Each migration is a small script describing one
step in changing the database schema, and how to undo it.

Always run the commands below from the `server/` folder (next to `app.py`) with `FLASK_APP=app.py` set
(`export FLASK_APP=app.py`).

## Folder layout

```
migration/
├── README.md          this file
├── alembic.ini        Alembic settings (logging, script location)
├── env.py             connects Alembic to the Flask app and its models
├── script.py.mako     template used to generate new migration files
└── version/          one file per schema change, in order
    ├── <id>_create_users_table.py
    └── <id>_create_notes_table.py
```

You normally only read `version/`. Leave `alembic.ini`, `env.py` and
`script.py.mako` alone unless you know why you are changing them.

## Folder names

This project uses `migration/` and `version/` (singular) instead of Flask-Migrate's
defaults (`migrations/` and `versions/`). Two settings make that work:

- `config.py` passes the folder: `Migrate(app, db, directory="migration")`
- `migration/alembic.ini` points Alembic at the scripts folder:
  `version_locations = %(here)s/version`

If you rename either folder, update the matching setting. If you don't, `flask db upgrade` fails
with "Path doesn't exist" or quietly applies nothing.

## How it works

1. **You change a model** in `models.py` (for example, add a column).
2. **`flask db migrate -m "message"`** compares your models with the current
   database and writes a new file into `version/` containing the difference.
3. **`flask db upgrade`** runs any migration that has not been applied yet.
4. Alembic records the latest applied revision in a table called
   `alembic_version` inside the database, so it always knows where the
   database stands.

### The revision chain

Every file has two identifiers near the top:

```python
revision = 'e810cdadd656'        # this migration's unique ID
down_revision = '498368395aa3'   # the migration that must run before it
```

Following `down_revision` links gives an ordered chain:

```
None -> create users table -> create notes table -> (next change...)
```

`upgrade` walks the chain forward from the revision stored in
`alembic_version`. `downgrade` walks it backward. **Never edit these IDs by
hand**, since a wrong value breaks the chain.

### Inside a migration file

```python
def upgrade():
    # apply the change (create tables, add columns, add indexes...)

def downgrade():
    # undo it, in reverse order
```

- `op.create_table(...)` builds a table. This is your model written out column
  by column, with its primary key and foreign key constraints.
- `batch_alter_table(...)` is used for changes to existing tables. SQLite has
  limited `ALTER TABLE` support, so Alembic rebuilds the table behind the
  scenes.
- Constraint names such as `fk_notes_user_id_users` and `pk_notes` come from the
  `naming_convention` in `config.py`. Named constraints are what let later
  migrations modify them on SQLite.

## Migrations in this project

| Order | Revision message | What it does |
|---|---|---|
| 1 | create users table | Creates `users` (`id`, unique `username`, `_password_hash`) |
| 2 | create notes table | Creates `notes` (`id`, `title`, `content`, `created_at`, `updated_at`, `user_id` foreign key to `users.id`, index on `user_id`) |

## Everyday commands

| Command | Purpose |
|---|---|
| `flask db upgrade` | Apply all pending migrations (use this on a fresh clone) |
| `flask db migrate -m "describe change"` | Generate a new migration from model changes |
| `flask db downgrade` | Undo the most recent migration |
| `flask db downgrade base` | Undo everything (empty schema) |
| `flask db current` | Show which revision the database is at |
| `flask db history` | List the migration chain |
| `flask db heads` | Show the newest revision(s) in `version/` |

## Making a schema change

```bash
# 1. edit models.py (e.g. add a column to Note)
flask db migrate -m "add pinned to notes"
# 2. open the new file in version/ and check it did what you expect
flask db upgrade
# 3. commit the new file in version/ with the model change
```

Autogenerate is a best guess. Always review the generated file. It can miss
things such as column renames (it sees a drop plus an add, which would lose
data) and changes to some constraints.

## Rules of thumb

- **Commit every file in `version/`** so everyone gets the same schema history.
- **Do not edit a migration that has been pushed or applied elsewhere.** Add a
  new one instead.
- **One logical change per migration**, with a clear `-m` message.
- **Never mix `db.create_all()` and migrations on the same database file.**
  `create_all()` creates tables without recording anything in
  `alembic_version`, so a later `flask db upgrade` fails with "table already
  exists". Pick one approach per database and delete `app.db` when switching.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `table users already exists` on upgrade | The tables were made with `create_all()`. Delete `app.db` (dev only) and run `flask db upgrade` again. |
| `Target database is not up to date` on migrate | Run `flask db upgrade` first, then `flask db migrate`. |
| `Can't locate revision identified by '...'` | The database points at a revision missing from `version/`. Delete `app.db` in dev, or restore the missing file. |
| Migration generated with no changes | The model was not imported. `app.py` imports `models`, so make sure `FLASK_APP=app.py` is set. |
| `Path doesn't exist: migrations` | `directory="migration"` is missing from `Migrate(...)` in `config.py`. |
| `flask db upgrade` prints no "Running upgrade" line | `version_locations` in `migration/alembic.ini` does not match the scripts folder name. |
| `No such command 'db'` | `FLASK_APP` is not set, or Flask-Migrate is not installed (run `pipenv install`). |
