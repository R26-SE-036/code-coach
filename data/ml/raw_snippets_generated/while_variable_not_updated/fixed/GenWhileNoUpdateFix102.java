public class GenWhileNoUpdateFix102 {
    static boolean isEven1(int total) {
        return total % 2 == 0;
    }

    static boolean isEven2(int quota) {
        return quota % 2 == 0;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static void printAll4(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int clamp6(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int gather(int count, int points) {
        int sum = 0;
        while (count < points) {
            sum += count;
            count++;
        }
        return sum;
    }

    static void printAll7(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int clamp8(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
