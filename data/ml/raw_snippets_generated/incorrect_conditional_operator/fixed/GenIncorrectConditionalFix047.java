public class GenIncorrectConditionalFix047 {
    static String report(boolean verified) {
        if (verified == true) {
            return "paid";
        }
        return "new";
    }

    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
