public class GenArrayIndexBug015 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static void stampLast(int[] weights, int value) {
        weights[weights.length] = value;
    }
}
