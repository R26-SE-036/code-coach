public class Clean013 {
    public boolean contains(String[] items, String target) {
        for (int i = 0; i < items.length; i++) {
            if (items[i].equals(target)) {
                return true;
            }
        }
        return false;
    }
}
