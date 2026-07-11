public class GenOffByOneBug037 {
    static int[] duplicate(int[] ages) {
        int[] copy = new int[ages.length];
        for (int i = 0; i <= ages.length; i++) {
            copy[i] = ages[i];
        }
        return copy;
    }

    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain3(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
