public class GenCleanGeneric119 {
    static boolean isEven1(int steps) {
        return steps % 2 == 0;
    }

    static int drain2(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
