package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix028 {
    public int getAbsoluteTail(int[] nums) {
        return Math.abs(nums[nums.length - 1]);
    }
}