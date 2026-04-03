public class Clean029 {
    public boolean allPositive(int[] nums) {
        for (int num : nums) {
            if (num <= 0) {
                return false;
            }
        }
        return true;
    }
}
