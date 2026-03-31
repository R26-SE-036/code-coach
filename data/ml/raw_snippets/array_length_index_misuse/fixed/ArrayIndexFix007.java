package data.ml.raw_snippets.array_length_index_misuse.fixed;

public class ArrayIndexFix007 {
    public static void main(String[] args) {
        int[] nums = { 3, 6, 9 };

        System.out.println(nums[nums.length - 1]);
    }
}
