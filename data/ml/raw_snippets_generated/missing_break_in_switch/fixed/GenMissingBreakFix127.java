public class GenMissingBreakFix127 {
    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int sum2(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int drain3(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static void printAll4(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }
}
