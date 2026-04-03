package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix019 {
    public int sumTail(int[] nums) {
        return nums[nums.length - 1] + nums[0];
    }
}