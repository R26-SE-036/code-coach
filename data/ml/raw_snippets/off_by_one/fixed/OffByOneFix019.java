package data.ml.raw_snippets.off_by_one.fixed;

public class OffByOneFix019 {
    public int countPositive(int[] nums) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] > 0)
                count++;
        }
        return count;
    }
}
