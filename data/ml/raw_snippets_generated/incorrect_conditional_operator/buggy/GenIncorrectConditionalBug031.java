public class GenIncorrectConditionalBug031 {
    static boolean matches(boolean open, boolean enabled) {
        if (open = enabled) {
            return true;
        }
        return false;
    }

    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
