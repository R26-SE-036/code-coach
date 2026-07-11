public class GenMissingBreakBug150 {
    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static boolean isEven2(int level) {
        return level % 2 == 0;
    }

    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
            case 2:
                label = "queued";
                break;
            case 3:
                label = "new";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int drain3(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static boolean isEven4(int attempts) {
        return attempts % 2 == 0;
    }
}
