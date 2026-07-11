public class GenCleanGeneric011 {
    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
