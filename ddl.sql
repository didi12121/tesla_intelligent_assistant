CREATE TABLE `tesla_partner_account` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `domain` VARCHAR(255) NOT NULL,
  `account_id` VARCHAR(128) NOT NULL,
  `name` VARCHAR(255) DEFAULT NULL,
  `description` VARCHAR(1000) DEFAULT NULL,
  `public_key_hex` TEXT DEFAULT NULL,
  `public_key_pem_url` VARCHAR(500) DEFAULT NULL,
  `is_active` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_domain` (`domain`),
  UNIQUE KEY `uk_account_id` (`account_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla partner account';

CREATE TABLE `tesla_partner_token` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `client_id` VARCHAR(255) NOT NULL,
  `access_token` TEXT NOT NULL,
  `token_type` VARCHAR(50) DEFAULT NULL,
  `expires_in` INT DEFAULT NULL,
  `expires_at` DATETIME DEFAULT NULL,
  `scope` VARCHAR(1000) DEFAULT NULL,
  `audience` VARCHAR(500) DEFAULT NULL,
  `is_latest` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_partner_client_latest` (`client_id`,`is_latest`),
  KEY `idx_partner_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla partner access tokens';

CREATE TABLE `tesla_oauth_session` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id',
  `state` VARCHAR(255) NOT NULL,
  `nonce` VARCHAR(255) NOT NULL,
  `redirect_uri` VARCHAR(500) NOT NULL,
  `scopes` VARCHAR(2000) DEFAULT NULL,
  `authorize_url` TEXT DEFAULT NULL,
  `status` VARCHAR(50) NOT NULL DEFAULT 'CREATED',
  `code` VARCHAR(1000) DEFAULT NULL,
  `error_message` VARCHAR(2000) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_state` (`state`),
  KEY `idx_oauth_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla OAuth sessions';

CREATE TABLE `tesla_third_party_token` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id',
  `client_id` VARCHAR(255) NOT NULL,
  `tesla_user_sub` VARCHAR(255) DEFAULT NULL,
  `access_token` TEXT NOT NULL,
  `refresh_token` TEXT DEFAULT NULL,
  `id_token` TEXT DEFAULT NULL,
  `token_type` VARCHAR(50) DEFAULT NULL,
  `expires_in` INT DEFAULT NULL,
  `access_token_expires_at` DATETIME DEFAULT NULL,
  `scope` VARCHAR(2000) DEFAULT NULL,
  `audience` VARCHAR(500) DEFAULT NULL,
  `oauth_state` VARCHAR(255) DEFAULT NULL,
  `is_latest` TINYINT NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_third_client_latest` (`client_id`,`is_latest`),
  KEY `idx_third_user_latest` (`user_id`,`is_latest`),
  KEY `idx_third_expires_at` (`access_token_expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla third-party tokens';
CREATE TABLE `tesla_vehicle` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id',
  `client_id` VARCHAR(255) NOT NULL COMMENT 'Tesla client_id',
  `tesla_user_sub` VARCHAR(255) DEFAULT NULL COMMENT 'Tesla 用户标识，可空',
  `vin` VARCHAR(64) NOT NULL COMMENT '车辆 VIN',
  `vehicle_id` BIGINT DEFAULT NULL COMMENT 'Tesla vehicle_id',
  `id_s` VARCHAR(64) DEFAULT NULL COMMENT 'Tesla id_s',
  `display_name` VARCHAR(255) DEFAULT NULL COMMENT '车辆显示名称',
  `state` VARCHAR(64) DEFAULT NULL COMMENT '车辆在线状态',
  `in_service` TINYINT DEFAULT NULL COMMENT '是否服务状态',
  `api_version` INT DEFAULT NULL COMMENT 'API 版本',
  `raw_json` LONGTEXT DEFAULT NULL COMMENT '原始返回 JSON',
  `is_active` TINYINT NOT NULL DEFAULT 1 COMMENT '是否有效',
  `last_synced_at` DATETIME DEFAULT NULL COMMENT '最近同步时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_vin` (`vin`),
  KEY `idx_client_id` (`client_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_vehicle_id` (`vehicle_id`),
  KEY `idx_id_s` (`id_s`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla 车辆基础信息';

CREATE TABLE IF NOT EXISTS `tesla_app_user` (
  `id`            BIGINT NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(64) NOT NULL,
  `password_hash` VARCHAR(128) NOT NULL,
  `is_active`     TINYINT NOT NULL DEFAULT 1,
  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='应用用户';

CREATE TABLE IF NOT EXISTS `tesla_chat_message` (
  `id`         BIGINT NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT NOT NULL COMMENT '关联 tesla_app_user.id',
  `role`       VARCHAR(16) NOT NULL COMMENT 'user 或 assistant',
  `content`    TEXT NOT NULL COMMENT '消息内容',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_chat_user_created` (`user_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息记录';



● -- tesla_oauth_session 加 user_id
  ALTER TABLE `tesla_oauth_session` ADD COLUMN `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id' AFTER `id`;
  ALTER TABLE `tesla_oauth_session` ADD KEY `idx_oauth_user_id` (`user_id`);

  -- tesla_third_party_token 加 user_id
  ALTER TABLE `tesla_third_party_token` ADD COLUMN `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id' AFTER `id`;
  ALTER TABLE `tesla_third_party_token` ADD KEY `idx_third_user_latest` (`user_id`, `is_latest`);

  -- tesla_vehicle 加 user_id
  ALTER TABLE `tesla_vehicle` ADD COLUMN `user_id` BIGINT NOT NULL COMMENT '关联 tesla_app_user.id' AFTER `id`;
  ALTER TABLE `tesla_vehicle` ADD KEY `idx_user_id` (`user_id`);

CREATE TABLE IF NOT EXISTS `tesla_vehicle_telemetry` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT 'link tesla_app_user.id',
  `vin` VARCHAR(64) NOT NULL COMMENT 'vehicle VIN',
  `event_ts` DATETIME NOT NULL COMMENT 'telemetry event timestamp',
  `speed_kph` DECIMAL(8,2) DEFAULT NULL COMMENT 'speed km/h',
  `odometer_km` DECIMAL(12,3) DEFAULT NULL COMMENT 'odometer km',
  `battery_level` DECIMAL(5,2) DEFAULT NULL COMMENT 'battery level %',
  `latitude` DECIMAL(10,6) DEFAULT NULL,
  `longitude` DECIMAL(10,6) DEFAULT NULL,
  `raw_payload` JSON DEFAULT NULL COMMENT 'raw telemetry payload',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_telemetry_user_ts` (`user_id`, `event_ts`),
  KEY `idx_telemetry_vin_ts` (`vin`, `event_ts`),
  KEY `idx_telemetry_user_vin_ts` (`user_id`, `vin`, `event_ts`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tesla vehicle telemetry points';
