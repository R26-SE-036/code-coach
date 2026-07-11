public class GenCleanGeneric057 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int drain2(int stock) {
        int handled = 0;
        while (stock > 0) {
            handled += stock;
            stock--;
        }
        return handled;
    }

    static int drain3(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int sum5(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }
}
