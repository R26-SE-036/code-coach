public class GenIncorrectConditionalFix085 {
    static boolean matches(boolean loaded, boolean ready) {
        if (loaded == ready) {
            return true;
        }
        return false;
    }

    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
