SET timezone TO 'Europe/Moscow';

CREATE TYPE "sex_enum" AS ENUM (
  'male',
  'female'
);

CREATE TYPE "case_status" AS ENUM (
  'pending',
  'accepted',
  'rejected'
);

CREATE TYPE "payload_stage" AS ENUM (
  'before',
  'coloring',
  'after',
  'other'
);

CREATE TYPE "payload_status" AS ENUM (
  'pending',
  'accepted',
  'rejected',
  'edited'
);

CREATE TYPE "image_status" AS ENUM (
  'pending',
  'accepted',
  'rejected',
  'edited'
);

CREATE TABLE IF NOT EXISTS "patient" (
  "id" uuid NOT NULL UNIQUE,
  "age" text NOT NULL,
  "sex" sex_enum NOT NULL,
  PRIMARY KEY ("id")
);

CREATE TABLE "case" (
  "id" bigserial UNIQUE PRIMARY KEY,
  "patient_id" uuid UNIQUE,
  "type" int8 NOT NULL,
  "status" case_status NOT NULL,
  "sent_to_cvat_at" timestamp
);

CREATE TABLE "payload" (
  "id" bigserial UNIQUE PRIMARY KEY,
  "case_id" bigserial NOT NULL,
  "stage" payload_stage NOT NULL,
  "status" payload_status NOT NULL,
  "doctor_email" text NOT NULL,
  "upload_time" timestamp DEFAULT (now())
);


CREATE TABLE "image" (
  "id" UUID UNIQUE PRIMARY KEY,
  "payload_id" bigserial NOT NULL,
  "status" image_status NOT NULL,
  "s3_path" text NOT NULL,
  "device_name" text NOT NULL,
  "comment" text
);

ALTER TABLE "case" ADD FOREIGN KEY ("patient_id") REFERENCES "patient" ("id");

ALTER TABLE "payload" ADD FOREIGN KEY ("case_id") REFERENCES "case" ("id");

ALTER TABLE "image" ADD FOREIGN KEY ("payload_id") REFERENCES "payload" ("id");

CREATE OR REPLACE FUNCTION check_non_sent_cases()
RETURNS TRIGGER AS $$
DECLARE
    accepted_count INT;
BEGIN
    IF NEW.status = 'accepted' THEN
        SELECT COUNT(*) INTO accepted_count
        FROM "case"
        WHERE sent_to_cvat_at IS NULL AND status = 'accepted';

        IF accepted_count > 10 THEN
            PERFORM pg_notify('sent_to_cvat_notify', 'start');
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_on_update
AFTER UPDATE OF status ON "case"
FOR EACH ROW
EXECUTE FUNCTION check_non_sent_cases();
