create table users
(
    id    int auto_increment primary key,
    name  varchar(20)  not null unique,
    email varchar(254) not null unique,
    role  int          not null default 1,
    cover text         not null check (cover <> ''),
    hash  text         not null
);

create table tokens
(
    id      int auto_increment primary key,
    token   varchar(255) NOT NULL,
    user_id int          not null references users (id)
);

create table images
(
    id          int auto_increment primary key,
    user_id     int          not null references users (id),
    filename    varchar(255) not null,
    description text,
    published_at timestamp not null default current_timestamp
);