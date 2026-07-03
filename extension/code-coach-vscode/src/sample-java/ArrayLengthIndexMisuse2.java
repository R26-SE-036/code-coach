public class ArrayLengthIndexMisuse2 {
    public static void main(String[] args) {
        String[] cities = { "Karachi", "Lahore", "Islamabad" };
        System.out.println("Last city: " + cities[cities.length]);
    }
}
