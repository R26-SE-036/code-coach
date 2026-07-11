public class GenIncorrectConditionalFix035 {
    static String report(boolean verified) {
        if (verified == true) {
            return "expired";
        }
        return "final";
    }

    static String describe1(int count) {
        if (count < 10) {
            return "low";
        } else if (count > 50) {
            return "high";
        }
        return "medium";
    }

    static int largest2(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }
}
