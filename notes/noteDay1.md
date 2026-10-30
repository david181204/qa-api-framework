linux常用命令
pwd    显示当前目录
ls -la   列出所有文件
cd /tmp  切换目录
mkdir qa_test  创建目录
touch a.txt  创建空文件
echo "hello world" > a.txt  将“hello world”写入a.txt
cat a.txt   查看文件并显示
grep "hello" a.txt  搜索包含hello的行
tail -n 1 a.txt  查看最后一行并显示
ps aux    显示所有进程
ss -lntp   查看监听端口和对应进程（Git Bash 不支持，用 netstat -ano 或 Docker Ubuntu）
tail -f a.txt  实时跟踪文件新增内容，Ctrl+C 退出（排障看日志常用）
