public class GenCleanStackedLabels008 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static boolean isEven2(int total) {
        return total % 2 == 0;
    }

    static int drain3(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "paid";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
