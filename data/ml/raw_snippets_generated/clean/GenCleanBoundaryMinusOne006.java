public class GenCleanBoundaryMinusOne006 {
    static String describe1(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] ratings) {
        int total = 0;
        for (int i = 0; i <= ratings.length - 1; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int drain2(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }
}
