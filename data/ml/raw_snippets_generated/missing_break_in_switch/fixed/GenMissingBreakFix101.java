public class GenMissingBreakFix101 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "queued";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static String describe1(int attempts) {
        if (attempts < 5) {
            return "low";
        } else if (attempts > 20) {
            return "high";
        }
        return "medium";
    }

    static int drain2(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int drain3(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int sum4(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
