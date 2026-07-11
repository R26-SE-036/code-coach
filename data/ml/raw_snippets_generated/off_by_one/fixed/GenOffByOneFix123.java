public class GenOffByOneFix123 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int countAbove(int[] values, int threshold) {
        int hits = 0;
        for (int i = 0; i < values.length; i++) {
            if (values[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
