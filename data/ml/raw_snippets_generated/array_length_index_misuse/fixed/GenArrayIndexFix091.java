public class GenArrayIndexFix091 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static void showLast(int[] prices) {
        System.out.println(prices[prices.length - 1]);
    }

    static int drain2(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String describe3(int points) {
        if (points < 10) {
            return "low";
        } else if (points > 50) {
            return "high";
        }
        return "medium";
    }
}
