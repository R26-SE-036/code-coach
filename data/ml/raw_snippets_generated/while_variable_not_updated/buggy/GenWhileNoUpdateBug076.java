public class GenWhileNoUpdateBug076 {
    static int gather(int budget, int total) {
        int sum = 0;
        while (budget < total) {
            sum += budget;
        }
        return sum;
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

    static String describe2(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }
}
