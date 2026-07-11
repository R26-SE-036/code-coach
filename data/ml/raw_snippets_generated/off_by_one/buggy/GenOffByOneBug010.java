public class GenOffByOneBug010 {
    static int drain1(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static int addUp(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static String describe2(int total) {
        if (total < 5) {
            return "low";
        } else if (total > 20) {
            return "high";
        }
        return "medium";
    }
}
