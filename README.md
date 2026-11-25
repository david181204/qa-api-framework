依赖安装：（换新环境时使用）
激活虚拟环境后，安装所有依赖包：
pip install -r requirements.txt
一、启动数据库（Docker）
1.确保 Docker Desktop 开启
2.打开终端，启动 MySQL 容器：
docker start mysql-test
3.验证容器是否在运行（状态必须是 Up，端口是 3307->3306）：[我的大脑3306端口被占用]
docker ps
二、启动被测服务（终端A）
新开一个终端（专门用来跑服务，保持开启状态）
1.进入项目目录：
cd D:\qa-study
2.激活虚拟环境：
.\.venv\Scripts\Activate.ps1
3.启动FastAPI服务：
uvicorn app.main:app --reload --port 8000
三、执行测试/生成报告(终端B，习惯使用vscode内置)
进入项目目录，并启动虚拟环境：
cd D:\qa-study
.\.venv\Scripts\Activate.ps1
1.（1）跑全量测试，看结果：
pytest tests -v
（2）如果想跑某个文件或特定用例：
pytest tests/test_login.py -v
pytest tests/test_login.py::TestLogin::test_login_success -v
2.跑测试并生成 Allure 可视化报告：
（1）生成并临时预览报告（依赖本地启动 Server）：
pytest tests -v --alluredir=./allure-results
allure serve ./allure-results
（2）生成纯静态HTML报告：
allure generate ./allure-results -o ./allure-report --clean
allure open ./allure-report
3.推送到github：
git status                      #查看修改了哪些文件
git add .
git commit -m "feat: 修改的内容"
git push origin main            # 推送到 GitHub，自动触发 Actions 云端流水线
github端口变化命令：
git config --global http.proxy http://127.0.0.1:新端口
git config --global https.proxy http://127.0.0.1:新端口
(如果不需要代理，或在公司内网，可用 git config --global --unset http.proxy 取消)
