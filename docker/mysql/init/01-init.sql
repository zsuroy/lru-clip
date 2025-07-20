-- CLIP.LRU MySQL Database Initialization
-- This script is automatically executed when MySQL container starts for the first time

-- Set character set and collation for better Unicode support
ALTER DATABASE cliplru CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant additional privileges if needed
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON cliplru.* TO 'cliplru'@'%';
FLUSH PRIVILEGES;

-- Create a test connection to verify setup
SELECT 'MySQL database initialized successfully for CLIP.LRU' as status;
