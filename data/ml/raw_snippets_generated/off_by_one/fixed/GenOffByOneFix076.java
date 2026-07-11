public class GenOffByOneFix076 {
    static int[] duplicate(int[] sizes) {
        int[] copy = new int[sizes.length];
        for (int i = 0; i < sizes.length; i++) {
            copy[i] = sizes[i];
        }
        return copy;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String describe2(int count) {
        if (count < 100) {
            return "low";
        } else if (count > 500) {
            return "high";
        }
        return "medium";
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
