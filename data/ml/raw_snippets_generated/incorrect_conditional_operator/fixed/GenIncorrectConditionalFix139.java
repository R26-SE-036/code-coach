public class GenIncorrectConditionalFix139 {
    static String report(boolean loaded) {
        if (loaded == true) {
            return "shipped";
        }
        return "archived";
    }

    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
