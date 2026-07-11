public class GenCleanStackedLabels006 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
