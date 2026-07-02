create table users
(
    id    int auto_increment primary key,
    name  varchar(20)  not null unique,
    email varchar(254) not null unique,
    role  int          not null default 1,
    hash  text         not null,
    home  text         not null default '',
    style text         not null default ''
);

create table tokens
(
    id      int auto_increment primary key,
    token   varchar(255) NOT NULL,
    user_id int          not null references users (id)
);

create table pages
(
    id         int auto_increment primary key,
    user_id    int          not null references users (id),
    slug       varchar(255) not null,
    content    text,
    created_at timestamp    not null default current_timestamp,
    updated_at timestamp    not null DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    unique key (user_id, slug)
);