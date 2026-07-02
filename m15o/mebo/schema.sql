create table users(
       id int auto_increment primary key,
       name varchar(20) not null unique,
       email varchar(254) not null unique,
       role int not null default 1,
       cover text not null check (cover <> ''),
       hash text not null
);

create table threads(
       id int auto_increment primary key,
       title varchar(255) not null,
       content text not null check (content <> ''),
       published_at timestamp not null default current_timestamp,
       updated_at timestamp not null default current_timestamp,
       user_id int not null references users(id),
       sticky boolean not null default false
);

create table replies(
       id int auto_increment primary key,
       content text not null check (content <> ''),
       user_id int not null references users(id),
       published_at timestamp not null default current_timestamp,
       thread_id int not null references threads(id) on delete cascade
);

create table tokens(
       id int auto_increment primary key,
       token varchar(255) NOT NULL,
       user_id int not null references users(id)
);
