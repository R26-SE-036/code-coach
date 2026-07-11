public class GenOffByOneFix114 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int drain3(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
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

    static int countAbove(int[] ages, int threshold) {
        int hits = 0;
        for (int i = 0; i < ages.length; i++) {
            if (ages[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
