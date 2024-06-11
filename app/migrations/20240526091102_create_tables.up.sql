CREATE TABLE IF NOT EXISTS roles
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users(
    id SERIAL PRIMARY KEY,
    login VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name      VARCHAR(64) NOT NULL,
    last_name    VARCHAR(64) NOT NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW(),
    role_id       INT,
    CONSTRAINT fk_users_role_id
        FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE INDEX users_role_id
    ON users(role_id);

CREATE TABLE IF NOT EXISTS furniture(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL NOT NULL,
    image bytea,
    description TEXT
);

CREATE TABLE IF NOT EXISTS carts(
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    furniture_id INT NOT NULL,
    CONSTRAINT fk_carts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_carts_furniture_id
        FOREIGN KEY (furniture_id) REFERENCES furniture(id)
        ON DELETE CASCADE
);

CREATE INDEX carts_user_id
    ON carts(user_id);

CREATE TABLE IF NOT EXISTS orders(
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    datetime TIMESTAMP DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_orders_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX orders_user_id
    ON orders(user_id);

CREATE TABLE IF NOT EXISTS orders_furniture(
    order_id INT NOT NULL,
    furniture_id INT NOT NULL,
    PRIMARY KEY (order_id, furniture_id),
    CONSTRAINT fk_orders_furniture_order_id
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_orders_furniture_furniture_id
        FOREIGN KEY (furniture_id) REFERENCES furniture(id)
        ON DELETE CASCADE
);