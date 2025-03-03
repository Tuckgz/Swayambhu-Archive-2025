import mongoose from "mongoose"
import dotenv from "dotenv"

dotenv.config()


const mongoURI = process.env.MONGO_URI.toString();

const connectDB = async () => {
    try { 
        await mongoose.connect(mongoURI);

        console.log("Connection Made to Mongodb");
    } catch (error) {
        console.error("Connecton Failed", error.message);
        process.exit(1);
    }
};

export default connectDB;