public class GenOffByOneBug144 {
    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int drain4(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int addUp(int[] marks) {
        int total = 0;
        for (int i = 0; i <= marks.length; i++) {
            total += marks[i];
        }
        return total;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int largest6(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static String join7(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
