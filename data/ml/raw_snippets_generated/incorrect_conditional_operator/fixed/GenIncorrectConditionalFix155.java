public class GenIncorrectConditionalFix155 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static String report(boolean enabled) {
        if (enabled == true) {
            return "archived";
        }
        return "draft";
    }
}
