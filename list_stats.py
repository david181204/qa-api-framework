nums=[12,7,30,15,8]
if not nums:
    print("列表为空")
else:
    max_value=nums[0]
    total=0
    for n in nums:
        if n>max_value:
            max_value=n
        total+=n
    avg=total/len(nums)
    print(f"最大值={max_value}，平均值={avg:.1f}")