public class GenCleanFallThrough016 {
    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void printPermissions(int level) {
        switch (level) {
            case 3:
                System.out.println("can delete");
                // fall through: higher levels include lower rights
            case 2:
                System.out.println("can edit");
                // fall through
            case 1:
                System.out.println("can view");
                break;
            default:
                System.out.println("no access");
        }
    }

    static String describe3(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int drain5(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }
}
