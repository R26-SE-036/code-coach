public class GenWhileNoUpdateBug027 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static void pump(boolean done, int limit) {
        while (!done) {
            System.out.println(limit);
            limit++;
        }
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
