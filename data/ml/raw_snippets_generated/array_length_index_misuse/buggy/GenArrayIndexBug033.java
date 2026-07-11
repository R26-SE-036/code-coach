public class GenArrayIndexBug033 {
    static void stampLast(int[] weights, int value) {
        weights[weights.length] = value;
    }

    static int drain1(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
