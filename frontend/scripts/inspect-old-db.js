const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// 元のPythonアプリのデータベースパス
const oldDbPath = path.join(__dirname, '..', '..', 'Ganger', 'app', 'model', 'database_manager', 'Ganger.db');

console.log('元のデータベースパス:', oldDbPath);

// データベースを開く
const db = new sqlite3.Database(oldDbPath, sqlite3.OPEN_READONLY, (err) => {
  if (err) {
    console.error('データベース接続エラー:', err.message);
    return;
  }
  console.log('元のデータベースに接続しました');
});

// テーブル一覧を取得
db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, tables) => {
  if (err) {
    console.error('テーブル取得エラー:', err.message);
    return;
  }
  
  console.log('\n=== テーブル一覧 ===');
  tables.forEach(table => {
    console.log(`- ${table.name}`);
  });
  
  // 各テーブルの構造を確認
  let completed = 0;
  const totalTables = tables.length;
  
  tables.forEach(table => {
    db.all(`PRAGMA table_info(${table.name})`, (err, columns) => {
      if (err) {
        console.error(`テーブル ${table.name} 構造取得エラー:`, err.message);
        return;
      }
      
      console.log(`\n=== ${table.name} テーブル構造 ===`);
      columns.forEach(col => {
        console.log(`${col.name}: ${col.type} ${col.notnull ? 'NOT NULL' : ''} ${col.pk ? 'PRIMARY KEY' : ''}`);
      });
      
      // サンプルデータも確認（最初の3件）
      db.all(`SELECT * FROM ${table.name} LIMIT 3`, (err, rows) => {
        if (err) {
          console.error(`テーブル ${table.name} データ取得エラー:`, err.message);
        } else {
          console.log(`\n--- ${table.name} サンプルデータ (${rows.length}件) ---`);
          if (rows.length > 0) {
            console.log(JSON.stringify(rows, null, 2));
          }
        }
        
        completed++;
        if (completed === totalTables) {
          db.close((err) => {
            if (err) {
              console.error('データベース閉じるエラー:', err.message);
            } else {
              console.log('\nデータベースを閉じました');
            }
          });
        }
      });
    });
  });
});