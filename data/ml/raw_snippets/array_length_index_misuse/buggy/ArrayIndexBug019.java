public class ArrayIndexBug019 {
    public int sumTail(int[] nums) {
        return nums[nums.length] + nums[0];
    }
}