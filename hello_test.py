def check_score():
    raw = input("请输入分数：")

    try:
        score = float(raw)
    except ValueError:
        print("输入不是数字，请重新输入")
        return

    if score >= 60:
        print("通过")
    else:
        print("不通过")


if __name__ == "__main__":
    check_score()