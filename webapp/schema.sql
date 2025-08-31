CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    profile_pic TEXT NOT NULL,
    game_state TEXT NOT NULL,
    game_results TEXT NOT NULL
);
CREATE TABLE game_results (
    result_id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_date DATE NOT NULL,
    num_attempts INT NOT NULL,
    game_result VARCHAR(50),
)